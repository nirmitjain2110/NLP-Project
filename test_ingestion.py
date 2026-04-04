from ingestion import ingest_pdf

blocks=ingest_pdf("generic_test_document.pdf")

for b in blocks:
    print(b["type"],":",b["text"])