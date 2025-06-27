pip install .[dev]
bpm --help
export BPM_CACHE="/Users/ckuo/Desktop/bpm_cache"

# repo
bpm repo --help
bpm repo remove-repo UKA_IZKF_GF_repo
bpm repo add-repo https://github.com/IZKF-Genomics/BPM_repo
bpm repo add-repo /Users/ckuo/Desktop/BPM_repo
bpm repo list-repos
bpm repo repo-info UKA_IZKF_GF_repo

rm -rf demo/*

mkdir -p demo/250620_bcl_raw/
bpm generate demultiplexing:bclconvert --bcl-path demo/250620_bcl_raw/ --output demo/fastq/ --verbose

# init
bpm init --help
bpm init -f demo/230101_test --authors ckuo,lgan
bpm init -f demo/250101_Name1_Name2_Institute_Application --from demo/230101_test/project.yaml --authors lgan
rm -r demo/230101_test

# generate
bpm generate --help
bpm generate demultiplexing:bclconvert --help

bpm generate demultiplexing:bclconvert --output demo/250612_NBTEST --bcl-path demo/250620_bcl_raw/
bpm generate demultiplexing:bclconvert --project demo/250101_Name1_Name2_Institute_Application/project.yaml
bpm generate demultiplexing:bclconvert --project demo/250101_Name1_Name2_Institute_Application/project.yaml --bcl-path demo/250620_bcl_raw/
mkdir -p demo/250101_Name1_Name2_Institute_Application/bclconvert/fastq/
touch demo/250101_Name1_Name2_Institute_Application/bclconvert/fastq/test.fastq.gz
touch demo/250101_Name1_Name2_Institute_Application/bclconvert/fastq/test2.fastq.gz
touch demo/250101_Name1_Name2_Institute_Application/bclconvert/multiqc_report.html
bpm update --help
bpm update --template demultiplexing:bclconvert --project demo/250101_Name1_Name2_Institute_Application/project.yaml

bpm generate nfcore:rnaseq --help
# # bpm generate nfcore:rnaseq --project demo/250101_Name1_Name2_Institute_Application/project.yaml --verbose

# bpm run generate_nfcore_rnaseq_samplesheet --help