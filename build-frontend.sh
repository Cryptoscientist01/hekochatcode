#!/bin/bash

# HekoChat - Frontend Build Script for Hostinger
# Run this locally before uploading to Hostinger

set -e

echo "=========================================="
echo "HekoChat - Building Frontend for Hostinger"
echo "=========================================="

# Check if backend URL is provided
BACKEND_URL=${1:-"https://your-backend-url.railway.app"}

echo ""
echo "Backend URL: $BACKEND_URL"
echo ""

# Navigate to frontend
cd "$(dirname "$0")/frontend"

# Create production .env
echo "Creating production environment..."
cat > .env << EOF
REACT_APP_BACKEND_URL=$BACKEND_URL
REACT_APP_VAPID_PUBLIC_KEY=BMpQT6udu_oCEeMA3TzLdekSj0194hIy6wuYD2fCg4JZmje3VCgLL2W1pTEy-UIqeugpzfVtRytCxqzyQ7qGdBI
EOF

# Install dependencies
echo "Installing dependencies..."
yarn install

# Build
echo "Building for production..."
yarn build

# Copy .htaccess to build folder
echo "Adding .htaccess for React routing..."
cp .htaccess build/

# Create zip for easy upload
echo "Creating upload package..."
cd build
zip -r ../../hekochat-frontend.zip ./*
cd ..

echo ""
echo "=========================================="
echo "Build Complete!"
echo "=========================================="
echo ""
echo "Upload Instructions:"
echo "1. Login to Hostinger hPanel"
echo "2. Go to File Manager → public_html"
echo "3. Delete all existing files in public_html"
echo "4. Upload and extract: hekochat-frontend.zip"
echo "   OR upload all files from: frontend/build/"
echo ""
echo "Don't forget to upload .htaccess file!"
echo ""
