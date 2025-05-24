#!/usr/bin/env bash
# exit on error
set -o errexit

# Set the project directory
PROJECT_DIR="/opt/render/project/src"
cd $PROJECT_DIR

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

# Create static directories
echo "Creating static directories..."
mkdir -p $PROJECT_DIR/staticfiles
mkdir -p $PROJECT_DIR/static
chmod -R 755 $PROJECT_DIR/staticfiles
chmod -R 755 $PROJECT_DIR/static

# Run migrations
echo "Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create start script
echo "Creating start script..."
cat > $PROJECT_DIR/start.sh << 'EOF'
#!/usr/bin/env bash
set -e

# Activate virtual environment
source /opt/render/project/src/.venv/bin/activate

# Start uvicorn
exec /opt/render/project/src/.venv/bin/uvicorn talentsearch.asgi:application --host 0.0.0.0 --port 10000 --workers 4
EOF

# Make start script executable
chmod +x $PROJECT_DIR/start.sh

echo "Build completed successfully!"
