# Run isort
echo "Running isort"
isort --settings-path ./pyproject.toml app tests

# Run black
echo "Running black"
black --target-version py311 app tests

# Run pylint
echo "Running pylint"
pylint --rcfile=./.pylintrc app tests

# Run mypy
echo "Running mypy"
mypy --config-file pyproject.toml --show-error-codes app tests
