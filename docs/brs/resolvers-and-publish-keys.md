---
title: Resolvers & Publish Keys
parent: BRS
nav_order: 6
has_toc: true
---

# Resolvers & Publish Keys

Name important outputs and provide a small function to find each one.

## In the template
```
publish:
  fastq_dir:
    resolver: resolvers.fastq:main
  multiqc_report:
    resolver: resolvers.reports:find
    args: {pattern: "**/multiqc_report.html"}
```

## Resolver signature
```
# resolvers/fastq.py
def main(ctx):
    # Return an absolute path to the FASTQ directory
    return f"{ctx.project_dir}/{ctx.project.name}/{ctx.template.id}/fastq"
```

## Result in project.yaml
```
templates:
  - id: hello
    published:
      fastq_dir: /abs/250903_TEST/hello/fastq
```

## Naming rules
- Use short, stable `snake_case` keys: `fastq_dir`, `bam_dir`, `vcf`, `multiqc_report`.
- Document the type/shape (dir, file, URL, table) in your template README.
