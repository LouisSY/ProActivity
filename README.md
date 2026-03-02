# ProActivity / ProVoice

## How to use
1. Please install [uv package manager](https://docs.astral.sh/uv/getting-started/installation/) and [carla](https://carla.readthedocs.io/en/latest/start_quickstart/)
   - Note that Carla 0.9.16 is required
2. Run `CarlaUE4.exe -quality-level=Low`, execute in project root directory
3. In this project, run `uv sync` when it is your first time to install dependencies
4. Run `python .\src\drive\drive_test.py` to start driving vehicle manually
5. Run `uv run provoice participantid=001 environment=city secondary_task=none functionname="Adjust seat positioning" modeltype=combined state_model=xlstm w_fcd=0.7` in another terminal.
   - `python src/ProVoice/main.py participantid=001 environment=city secondary_task=none functionname="Adjust seat positioning" modeltype=combined state_model=xlstm w_fcd=0.7`
6. Web UI dashboard will be available at `http://127.0.0.1:8001`
7. Data will be saved in `data` directory
   - `data/decisions.csv`
   - `data/raw_data.jsonl`


## Documentation
- Mac setup guide (Apple Silicon): [docs/README_Setups_on_Mac.md](docs/README_Setups_on_Mac.md)
- Original README (archived): [docs/README_original.md](docs/README_original.md)
