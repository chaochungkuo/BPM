#!/bin/bash
# BPM Template: demultiplexing/bclconvert

# Enable strict mode: exit on error, undefined vars, and pipeline failures
set -euo pipefail

# Run bcl-convert
echo "🚀 Running bcl-convert..."
bcl-convert \
  --bcl-input-directory "/Users/ckuo/Desktop/BPM/demo/250620_bcl_raw" \
  --output-directory out_fastq \
  --sample-sheet samplesheet.csv \
  --no-lane-splitting true \
  --bcl-num-conversion-threads 2 \
  --bcl-num-compression-threads 2 \
  --bcl-num-decompression-threads 2
# --bcl-sampleproject-subdirectories true \

# Run FASTQC
echo "🔬 Running FASTQC..."
mkdir -p /fastqc
find  -maxdepth 2 -name "*.fastq.gz" | parallel -j 7  {} -o /fastqc

# Conditionally run fastq_screen
echo "🔎 Running fastq_screen..."
mkdir -p /fastq_screen
find  -maxdepth 2 -name "*.fastq.gz" | parallel -j 7  --outdir /fastq_screen {}

# Run MultiQC
echo "📊 Running MultiQC..."
mkdir -p /multiqc
 -f  -o /multiqc

# Cleanup
echo "🧹 Cleaning up..."
rm -rf /fastqc
[[ -d /fastq_screen ]] && rm -rf /fastq_screen

echo "✅ Done."

bpm update --template demultiplexing:bclconvert --project ./project.yaml
