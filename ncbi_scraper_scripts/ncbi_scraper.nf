#!/usr/bin/env nextflow

/*
 * NCBI/PMC Open Access Paper Scraper Pipeline
 * 
 * This pipeline downloads metadata for all open access papers from PMC,
 * filters by target journals, and optionally downloads full-text articles.
 */

nextflow.enable.dsl = 2

// Parameters
params.journals = null              // Comma-separated list of journal names
params.journal_file = null          // File containing journal names (one per line)  
params.output_dir = "results"       // Output directory
params.download_fulltext = false    // Whether to download full-text articles
params.max_articles = null          // Maximum number of articles to download (for testing)
params.case_sensitive = false       // Case-sensitive journal matching
params.list_journals_only = false   // Only list available journals and exit

// Validate parameters
if (!params.journals && !params.journal_file && !params.list_journals_only) {
    error "Error: Must specify either --journals or --journal_file parameter"
}

log.info """
    NCBI/PMC Open Access Scraper Pipeline
    =====================================
    Output directory    : ${params.output_dir}
    Target journals     : ${params.journals ?: 'from file: ' + params.journal_file}
    Download full-text  : ${params.download_fulltext}
    Max articles        : ${params.max_articles ?: 'unlimited'}
    Case sensitive      : ${params.case_sensitive}
    List journals only  : ${params.list_journals_only}
    """

/*
 * Process 1: Download PMC metadata
 */
process FETCH_PMC_METADATA {
    publishDir "${params.output_dir}/metadata", mode: 'copy'
    
    output:
    path "pmc_oa_file_list.csv", emit: metadata
    
    script:
    """
    source ${projectDir}/venv/bin/activate
    python3 ${projectDir}/fetch_pmc_metadata.py .
    """
}

/*
 * Process 2: List available journals (optional)
 */
process LIST_JOURNALS {
    publishDir "${params.output_dir}/metadata", mode: 'copy'
    
    input:
    path metadata
    
    output:
    path "journal_counts.csv", emit: journal_counts
    
    when:
    params.list_journals_only
    
    script:
    """
    source ${projectDir}/venv/bin/activate
    python3 ${projectDir}/filter_by_journals.py ${metadata} \\
        --list-journals \\
        --top-journals 500 \\
        --output journal_counts.csv
    """
}

/*
 * Process 3: Filter metadata by target journals
 */
process FILTER_BY_JOURNALS {
    publishDir "${params.output_dir}/filtered", mode: 'copy'
    
    input:
    path metadata
    path journal_file, stageAs: 'journal_list.txt'
    
    output:
    path "filtered_pmc_metadata.csv", emit: filtered_metadata
    path "filter_stats.txt", emit: filter_stats
    
    when:
    !params.list_journals_only
    
    script:
    def journal_args = ""
    if (params.journals) {
        def journal_list = params.journals.split(',').collect { "'${it.trim()}'" }.join(' ')
        journal_args = "--journals ${journal_list}"
    }
    if (params.journal_file) {
        journal_args += " --journal-file journal_list.txt"
    }
    
    def case_flag = params.case_sensitive ? "--case-sensitive" : ""
    
    """
    source ${projectDir}/venv/bin/activate
    python3 ${projectDir}/filter_by_journals.py ${metadata} \\
        ${journal_args} \\
        ${case_flag} \\
        --output filtered_pmc_metadata.csv \\
        2>&1 | tee filter_stats.txt
    """
}

/*
 * Process 4: Prepare download list (limit if specified)
 */
process PREPARE_DOWNLOAD_LIST {
    publishDir "${params.output_dir}/download_lists", mode: 'copy'
    
    input:
    path filtered_metadata
    
    output:
    path "download_list.csv", emit: download_list
    path "download_stats.txt", emit: download_stats
    
    when:
    params.download_fulltext && !params.list_journals_only
    
    script:
    def limit_cmd = params.max_articles ? "head -n \$((${params.max_articles} + 1))" : "cat"
    
    """
    echo "Preparing download list from filtered metadata..." > download_stats.txt
    echo "Original articles: \$(tail -n +2 ${filtered_metadata} | wc -l)" >> download_stats.txt
    
    # Limit articles if specified
    ${limit_cmd} ${filtered_metadata} > download_list.csv
    
    echo "Articles to download: \$(tail -n +2 download_list.csv | wc -l)" >> download_stats.txt
    
    # Show sample of articles
    echo "" >> download_stats.txt
    echo "Sample articles:" >> download_stats.txt
    head -n 6 download_list.csv >> download_stats.txt
    """
}

/*
 * Process 5: Download full-text articles (optional)
 */
process DOWNLOAD_ARTICLES {
    publishDir "${params.output_dir}/articles", mode: 'copy'
    maxForks 3  // Limit concurrent downloads to be respectful to NCBI servers
    
    input:
    path download_list
    
    output:
    path "articles/", emit: articles, optional: true
    path "download_log.txt", emit: download_log
    
    when:
    params.download_fulltext && !params.list_journals_only
    
    script:
    """
    mkdir -p articles
    
    echo "Starting article downloads..." > download_log.txt
    echo "Download list: ${download_list}" >> download_log.txt
    echo "Started at: \$(date)" >> download_log.txt
    
    source ${projectDir}/venv/bin/activate
    python3 ${projectDir}/download_articles.py \\
        --metadata ${download_list} \\
        --output articles/ \\
        --log download_log.txt
    
    echo "Completed at: \$(date)" >> download_log.txt
    echo "Downloaded articles: \$(find articles/ -name '*.xml' | wc -l)" >> download_log.txt
    """
}

/*
 * Main workflow
 */
workflow {
    // Download metadata
    FETCH_PMC_METADATA()
    
    if (params.list_journals_only) {
        // Only list journals and exit
        LIST_JOURNALS(FETCH_PMC_METADATA.out.metadata)
    } else {
        // Prepare journal file input (create empty file if not provided)
        if (params.journal_file) {
            journal_file_ch = Channel.fromPath(params.journal_file, checkIfExists: true)
        } else {
            // Create empty file channel when no journal file is provided
            journal_file_ch = Channel.fromPath('/dev/null')
        }
        
        // Filter by target journals
        FILTER_BY_JOURNALS(FETCH_PMC_METADATA.out.metadata, journal_file_ch)
        
        if (params.download_fulltext) {
            // Prepare download list and download articles
            PREPARE_DOWNLOAD_LIST(FILTER_BY_JOURNALS.out.filtered_metadata)
            DOWNLOAD_ARTICLES(PREPARE_DOWNLOAD_LIST.out.download_list)
        }
    }
}

workflow.onComplete {
    log.info """
    Pipeline completed!
    ===================
    Status: ${workflow.success ? 'SUCCESS' : 'FAILED'}
    Duration: ${workflow.duration}
    Output directory: ${params.output_dir}
    """
    
    if (params.list_journals_only) {
        log.info "Check ${params.output_dir}/metadata/journal_counts.csv for available journals"
    } else {
        log.info "Check ${params.output_dir}/filtered/ for filtered metadata"
        if (params.download_fulltext) {
            log.info "Check ${params.output_dir}/articles/ for downloaded full-text articles"
        }
    }
}
