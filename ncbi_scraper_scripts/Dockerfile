# Use the official R base image
FROM r-base:4.3.2

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install required R packages
RUN R -e "install.packages(c('biorxivr', 'lubridate', 'dplyr'), repos='https://cran.rstudio.com/')"

# Install required Python packages
RUN pip3 install requests pandas PyMuPDF

# Copy the Nextflow scripts and supporting files
COPY ncbi_scraper.nf ./
COPY nextflow.config ./
COPY fetch_pmc_metadata.py ./
COPY filter_by_journals.py ./
COPY download_articles.py ./
COPY README.md ./

# Create directories for outputs
RUN mkdir -p results logs

# Set the default command
CMD ["R"]
