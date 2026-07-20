# Contributing to SOC Triage Agent

Thank you for your interest in contributing! 🎉

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/soc-triage-agent.git`
3. Create a virtual environment and install dependencies
4. Create a new branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # dev dependencies
```

## Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings to public functions
- Run `black` and `isort` before committing

## Testing

```bash
pytest tests/ -v --cov=app
```

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Ensure all tests pass
3. Update version numbers following [SemVer](https://semver.org/)
4. Your PR will be reviewed within 48 hours

## Questions?

Open an issue or reach out in Discussions!
