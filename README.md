# TFHE Artifact

This anonymous artifact contains the code used for the SetA to UniX
correctness check and for the SetA to UniX security validation with
Lattice Estimator. SetA denotes the parameter family widely adopted by the
classic TFHE scheme. UniX denotes the GLWE-based TFHE parameter family that
fixes `N` with hardware-friendly constraints.

## Layout

- `include/`: SetA to UniX parameter-pair inputs.
- `src/correctness/`: Rust examples for TFHE-rs SetA to UniX correctness
  validation.
- `src/security/`: Python security-validation driver.
- `test/`: Reproduction scripts for correctness and security validation.
- `third-party/`: Local copies of TFHE-rs and Lattice Estimator modules needed
  by the scripts.

### Security Validation

Mandatory requirements:

- Python 3.10 or later.
- Python packages used by the validation driver: `numpy`, `scipy`, and `mpmath`.
- Lattice Estimator must be available at `third-party/lattice-estimator`.
  The security command imports Lattice Estimator directly; if it is missing, the
  validation is not considered complete.

Install/check the required Python packages:

```powershell
python -m pip install numpy scipy mpmath
```

Check that Lattice Estimator is present:

```powershell
Test-Path third-party\lattice-estimator\estimator
```

If the command prints `False`, install Lattice Estimator into the required path:

```powershell
git clone https://github.com/malb/lattice-estimator third-party\lattice-estimator
```

Run the SetA to UniX security validation:

```powershell
python -B src\security\unix_parameter_security.py validate-seta-unix
```

Expected command-line summary:

```text
SetA-I   -> UniX-I   target 80/80,   pass=True, estimator overall 80.190/80.190
SetA-II  -> UniX-II  target 110/110, pass=True, estimator overall 110.096/110.096
SetA-III -> UniX-III target 128/128, pass=True, estimator overall 128.189/128.189
SetA-IV  -> UniX-IV  target 128/128, pass=True, estimator overall 128.189/128.189
SetA-V   -> UniX-V   target 128/128, pass=True, estimator overall 128.188/128.188
```

Use `--json` for a compact machine-readable result, or `--details` to print the
raw Lattice Estimator threshold details. The command prints results to stdout
only and does not write generated result files.

### Correctness Validation

Mandatory requirements:

- Rust/Cargo.
- The TFHE-rs checkout must be available at `third-party/tfhe-rs`, or set
  `TFHE_RS_DIR=/path/to/tfhe-rs`.

The correctness validation contains two small experiments: the original
GLWE-based correctness validation, and the UniX GLWE plus key-decompression
correctness validation.

#### GLWE Correctness

Run the SetA to UniX correctness validation:

```bash
bash test/run_seta_unix_correctness.sh
```

On Windows PowerShell, run the TFHE-rs example directly:

```powershell
cd third-party\tfhe-rs
cargo run --quiet -p tfhe --example unix_pbs_experiment --features shortint,software-prng -- --suite seta-unix
```

The command uses TFHE-rs to generate keys, encrypt one message, run one
programmable bootstrap, and decrypt once for each parameter. Each parameter is
run once, and the command exits with a non-zero status if any parameter set
fails. In the summaries, `standard=True` reports the baseline PBS path.

Expected command-line summary:

```text
SetA-I   correctness pass=True, standard=True
UniX-I   correctness pass=True, standard=True
SetA-II  correctness pass=True, standard=True
UniX-II  correctness pass=True, standard=True
SetA-III correctness pass=True, standard=True
UniX-III correctness pass=True, standard=True
SetA-IV  correctness pass=True, standard=True
UniX-IV  correctness pass=True, standard=True
SetA-V   correctness pass=True, standard=True
UniX-V   correctness pass=True, standard=True
```

Use `--json` to print full per-parameter details or `--verbose` to print key
generation progress. The correctness command prints results to stdout only and
does not write generated result files.

#### GLWE + Key Decompression Correctness

Run only the UniX GLWE plus key-decompression correctness validation. The
`--summary-tag` option only changes the printed summary name; the validation
logic is unchanged:

```bash
bash test/run_unix_key_decompression_correctness.sh
```

On Windows PowerShell:

```powershell
cd third-party\tfhe-rs
cargo run --quiet -p tfhe --example unix_pbs_experiment --features shortint,software-prng -- --suite seta-unix --scheme unix --summary-tag GLWE+key_decompression
```

The key-decompression PBS path is implemented as separate helper functions in
the TFHE-rs example. The code creates a compressed server key with
`CompressedServerKey::new(&cks)`, prepares a decompressed server key with
`prepare_decompressed_server_key`, and executes PBS with
`apply_pbs_with_decompressed_key`. In this experiment, `pass=True` requires the
standard PBS result and the decompressed-key PBS result to match and decrypt
correctly.

Expected UniX summary:

```text
UniX-I   correctness[GLWE+key_decompression] pass=True, standard=True
UniX-II  correctness[GLWE+key_decompression] pass=True, standard=True
UniX-III correctness[GLWE+key_decompression] pass=True, standard=True
UniX-IV  correctness[GLWE+key_decompression] pass=True, standard=True
UniX-V   correctness[GLWE+key_decompression] pass=True, standard=True
```

#### Optional Accuracy Sampling

Both correctness experiments can optionally repeat PBS several times on a
selected parameter and print an accuracy summary. Use `--entry-index` to select
one SetA/UniX pair, `--scheme` to select `seta`, `unix`, or `all`, and
`--trials` to set the number of bootstrap trials. The example below uses 10
trials to keep the test short; use `--trials 100` for a longer check.

GLWE correctness, UniX-I only:

```powershell
cd third-party\tfhe-rs
cargo run --quiet -p tfhe --example unix_pbs_experiment --features shortint,software-prng -- --suite seta-unix --scheme unix --entry-index 0 --trials 100
```

Expected summary:

```text
UniX-I   correctness pass=True, standard=True, accuracy=10/10 (100.00%)
```

GLWE plus key-decompression correctness, UniX-I only:

```powershell
cd third-party\tfhe-rs
cargo run --quiet -p tfhe --example unix_pbs_experiment --features shortint,software-prng -- --suite seta-unix --scheme unix --summary-tag GLWE+key_decompression --entry-index 0 --trials 100
```

Expected summary:

```text
UniX-I   correctness[GLWE+key_decompression] pass=True, standard=True, accuracy=10/10 (100.00%)
```

The correctness scripts require Rust/Cargo. The security script requires
Python with the mandatory Lattice Estimator dependency available. Set
`TFHE_RS_DIR=/path/to/tfhe-rs` to use another TFHE-rs checkout. All reproduction
scripts print results to stdout and do not save generated outputs.
