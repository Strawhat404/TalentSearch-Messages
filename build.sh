#!/usr/bin/env bash
# exit on error
set -o errexit

# Set the project directory
PROJECT_DIR="/opt/render/project/src"
cd $PROJECT_DIR

echo "Current directory: $(pwd)"
echo "Directory contents before setup:"
ls -la

# Remove existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create and activate virtual environment
echo "Creating virtual environment..."
python -m venv .venv
source .venv/bin/activate

# Upgrade pip and install dependencies
echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

# Install uvicorn explicitly
echo "Installing uvicorn..."
pip install "uvicorn[standard]==0.27.1"

# Create static directories and ensure they exist
echo "Creating static directories..."
mkdir -p static
mkdir -p staticfiles
chmod -R 755 static
chmod -R 755 staticfiles

# Verify static directories
echo "Verifying static directories..."
ls -la static
ls -la staticfiles

# Run migrations
echo "Running migrations..."
python manage.py makemigrations adverts --noinput
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create start script
echo "Creating start script..."
START_SCRIPT="$PROJECT_DIR/start.sh"
cat > "$START_SCRIPT" << 'EOF'
#!/usr/bin/env bash
set -e

echo "Starting server..."
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Activate virtual environment
echo "Activating virtual environment..."
source /opt/render/project/src/.venv/bin/activate

# Verify uvicorn installation
echo "Uvicorn location:"
which uvicorn

# Start uvicorn
echo "Starting uvicorn server..."
exec /opt/render/project/src/.venv/bin/uvicorn talentsearch.asgi:application --host 0.0.0.0 --port 10000 --workers 4
EOF

# Make start script executable
echo "Setting start script permissions..."
chmod +x "$START_SCRIPT"

# Verify start script
echo "Verifying start script..."
ls -l "$START_SCRIPT"
echo "Start script contents:"
cat "$START_SCRIPT"

echo "Build completed successfully!"
echo "Final directory contents:"
ls -la
