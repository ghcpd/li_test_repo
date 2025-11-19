# Example Scripts

This directory contains example shell scripts demonstrating different use cases of the Schedule Conflict Detection System.

## Scripts

### 1. run_all_algorithms.sh
Runs all three detection algorithms with full validation and visualization.

**Use when**: You want comprehensive analysis and algorithm comparison

```bash
cd examples
bash run_all_algorithms.sh
```

### 2. run_fast_algorithm.sh
Runs only the Sweep Line algorithm (fastest) without generating visualizations.

**Use when**: You need quick results for large datasets

```bash
cd examples
bash run_fast_algorithm.sh
```

### 3. run_single_person.sh
Analyzes conflicts for a specific person with filtered visualizations.

**Use when**: You want to focus on one individual's schedule

```bash
cd examples
# Edit the PERSON_ID variable in the script first
bash run_single_person.sh
```

## Making Scripts Executable

On Linux/Mac:
```bash
chmod +x *.sh
./run_all_algorithms.sh
```

## Windows Users

Use Git Bash or WSL, or run the Python command directly:

```cmd
python schedule_conflict_detector.py --input test_schedule.csv --known known_conflicts.json --output report/
```

## Customization

You can modify these scripts to:
- Change input/output file paths
- Adjust algorithm selection
- Add additional command-line options
- Integrate with your own workflow
