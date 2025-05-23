#!/bin/bash
# BPM Template: demultiplexing/bclconvert

set -euo pipefail

# System configuration
RESERVED_CORES=1  # Number of cores to reserve for system processes

# Get system CPU info
TOTAL_CORES=$(nproc)
AVAILABLE_CORES=$(( TOTAL_CORES - RESERVED_CORES > 0 ? TOTAL_CORES - RESERVED_CORES : 1 ))
IDLE_PCT=$(mpstat 1 1 | awk '/Average:/ && $12 ~ /[0-9.]+/ { print $12 }')
IDLE_CPUS=$(awk -v idle_pct="$IDLE_PCT" -v cores="$AVAILABLE_CORES" 'BEGIN { print int(idle_pct * cores / 100) }')
N_THREADS=$(( IDLE_CPUS / 3 ))

echo "🧠 Total cores: $TOTAL_CORES | Idle: ${IDLE_PCT}% | Threads: $N_THREADS"

# Run bcl-convert
echo "🚀 Running bcl-convert..."
{{ tool_paths.bclconvert }} \
  --bcl-input-directory "{{ bcl_path }}" \
  --output-directory out_fastq \
  --sample-sheet samplesheet.csv \
  --no-lane-splitting true \
  --bcl-num-conversion-threads "$N_THREADS" \
  --bcl-num-compression-threads "$N_THREADS" \
  --bcl-num-decompression-threads "$N_THREADS"
# --bcl-sampleproject-subdirectories true \

# Run FASTQC
echo "🔬 Running FASTQC..."
mkdir -p "{{ output_dir }}/fastqc"
find "{{ output_dir }}" -maxdepth 2 -name "*.fastq.gz" | parallel -j "$IDLE_CPUS" "{{ tool_paths.fastqc }} {} -o {{ output_dir }}/fastqc"

# Conditionally run fastq_screen
{% if run_fastq_screen %}
echo "🔎 Running fastq_screen..."
mkdir -p "{{ output_dir }}/fastq_screen"
find "{{ output_dir }}" -maxdepth 2 -name "*.fastq.gz" | parallel -j "$IDLE_CPUS" "{{ tool_paths.fastq_screen }} --outdir {{ output_dir }}/fastq_screen {}"
{% else %}
echo "⏭️ Skipping fastq_screen..."
{% endif %}

# Run MultiQC
echo "📊 Running MultiQC..."
mkdir -p "{{ output_dir }}/multiqc"
{{ tool_paths.multiqc }} -f "{{ output_dir }}" -o "{{ output_dir }}/multiqc"

# Cleanup
echo "🧹 Cleaning up..."
rm -rf "{{ output_dir }}/fastqc"
[[ -d "{{ output_dir }}/fastq_screen" ]] && rm -rf "{{ output_dir }}/fastq_screen"

echo "✅ Done."

bpm update --status completed --template demultiplexing/bclconvert project.yaml