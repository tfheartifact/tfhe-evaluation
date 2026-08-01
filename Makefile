.PHONY: all correctness key-decompression security

all: correctness security

correctness:
	bash test/run_seta_unix_correctness.sh

key-decompression:
	bash test/run_unix_key_decompression_correctness.sh

security:
	bash test/run_security_validation.sh
