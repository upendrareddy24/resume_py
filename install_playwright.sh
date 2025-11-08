#!/bin/bash

# Install Playwright for JavaScript rendering support

echo "📦 Installing Playwright for Meta & dynamic career pages..."
echo ""

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip not found. Please install Python first."
    exit 1
fi

# Step 1: Install Playwright package
echo "Step 1/2: Installing Playwright package..."
pip install playwright==1.48.2

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Playwright package"
    exit 1
fi

echo "✅ Playwright package installed"
echo ""

# Step 2: Install Chromium browser
echo "Step 2/2: Installing Chromium browser (this may take a minute)..."
python -m playwright install chromium

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Chromium browser"
    exit 1
fi

echo "✅ Chromium browser installed"
echo ""

# Verify installation
echo "Verifying installation..."
python -c "import playwright; print('✅ Playwright is ready!')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Playwright setup complete!"
    echo ""
    echo "You can now run:"
    echo "  python match.py --config config.json"
    echo ""
    echo "Meta jobs should now fetch full descriptions!"
else
    echo "⚠️  Installation may have issues. Try running manually:"
    echo "  python -m playwright install chromium"
fi

