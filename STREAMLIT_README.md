# HVAC Insulation Estimator - Streamlit SaaS Application

Professional web-based estimation tool for mechanical insulation contractors.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.30+-red.svg)

## Features

### 🎯 Core Capabilities
- **Specifications Management**: Manual entry or PDF extraction
- **Measurements Tracking**: Individual entry or bulk CSV import
- **Distributor Pricing**: Upload JSON, CSV, or Excel pricebooks
- **Real-time Calculations**: Instant material and labor estimates
- **Professional Quotes**: Export-ready quotes and material lists

### 📊 Advanced Features
- **Multiple File Formats**: JSON, CSV, Excel pricebook support
- **Configurable Markup**: Adjust profit margins on the fly
- **Labor Rate Customization**: Set your hourly rates
- **Contingency Control**: Configure project contingency percentage
- **Detailed Reporting**: Category breakdowns and cost analysis
- **Export Options**: TXT, CSV downloads for quotes and materials

### 🔧 Technical Features
- **Session Management**: Persistent data during workflow
- **Responsive Design**: Works on desktop and tablet
- **Professional UI**: Clean, intuitive interface
- **Error Handling**: Graceful fallbacks and user feedback
- **File Validation**: Smart column detection for imports

---

## Quick Start

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/glmoss-collab/PROINSULATIONESTIMATION.git
   cd PROINSULATIONESTIMATION
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Open in browser**
   ```
   http://localhost:8501
   ```

### Live Demo

Try the live application: [Coming Soon - Deploy to Streamlit Cloud]

---

## Usage Guide

### Step 1: Configure Pricing (Sidebar)

1. **Upload Distributor Pricebook** (Optional)
   - Supports: JSON, CSV, Excel formats
   - CSV/Excel should have columns: `item`/`material` and `price`/`cost`
   - Or use default hardcoded prices

2. **Set Markup Percentage**
   - Default: 15%
   - Adjustable: 0-100%

3. **Configure Labor Rate**
   - Default: $65/hour
   - Customize based on your market

4. **Set Contingency**
   - Default: 10%
   - Range: 0-20%

### Step 2: Add Specifications

#### Manual Entry
1. Select system type (duct, pipe, equipment)
2. Choose material (fiberglass, elastomeric, etc.)
3. Set thickness in inches
4. Add facing type (FSK, ASJ, or none)
5. Specify location (indoor, outdoor, exposed)
6. Check special requirements:
   - Aluminum jacketing
   - Mastic coating
   - Stainless bands
7. Click "Add Specification"

#### PDF Upload
1. Upload specification PDF
2. Click "Extract Specifications"
3. Review auto-extracted specs

### Step 3: Add Measurements

#### Manual Entry
1. Enter item ID (auto-generated)
2. Select system type
3. Input size (e.g., 12", 18x12, 2")
4. Enter length in linear feet
5. Specify location
6. Add fittings (elbows, tees, other)
7. Click "Add Measurement"

#### Bulk Import
1. Download `measurements_template.csv`
2. Fill in your measurements
3. Upload completed CSV
4. Click "Import Measurements"

### Step 4: Calculate Estimate

1. Review summary (specs + measurements)
2. Click "Calculate Estimate"
3. View real-time results:
   - Materials cost
   - Labor hours and cost
   - Total estimate
   - Category breakdown

### Step 5: Export Results

Download your deliverables:
- **Quote (TXT)**: Professional quote document
- **Material List (TXT)**: Distributor order list
- **Materials (CSV)**: Spreadsheet-ready data

---

## File Formats

### Pricebook Formats

#### JSON Format
```json
{
  "fiberglass_1.5": 4.10,
  "elastomeric_1.0": 4.10,
  "aluminum_jacket": 8.00,
  "mastic": 0.65
}
```

#### CSV Format
```csv
item,price
fiberglass_1.5,4.10
elastomeric_1.0,4.10
aluminum_jacket,8.00
mastic,0.65
```

#### Excel Format
| Material | Unit Price |
|----------|-----------|
| fiberglass_1.5 | 4.10 |
| elastomeric_1.0 | 4.10 |
| aluminum_jacket | 8.00 |
| mastic | 0.65 |

### Measurements CSV Template

Download `measurements_template.csv` or use this format:

```csv
item_id,system_type,size,length,location,elbows,tees
DUCT-001,duct,18x12,125.5,Main corridor,3,1
PIPE-001,pipe,2",75.0,Exterior wall,4,2
```

---

## Deployment

### Streamlit Community Cloud (FREE - Recommended)

1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Connect repository
4. Select `streamlit_app.py`
5. Deploy!

**See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide including:**
- Docker deployment
- Heroku deployment
- AWS deployment
- Custom domain setup
- Production optimization
- Scaling strategies

---

## Architecture

```
streamlit_app.py          # Main Streamlit UI application
├── hvac_insulation_estimator.py  # Core estimation engine
│   ├── SpecificationExtractor     # PDF spec extraction
│   ├── DrawingMeasurementExtractor # Measurement processing
│   ├── PricingEngine              # Distributor pricing & calculations
│   └── QuoteGenerator             # Quote and report generation
├── pricebook_sample.json  # Sample distributor pricing
├── requirements.txt       # Python dependencies
└── .streamlit/config.toml # Streamlit configuration
```

### Key Classes

**PricingEngine** - Enhanced with distributor support
- Multi-format pricebook loading (JSON, CSV, Excel)
- Intelligent price lookup with fallbacks
- Missing price tracking and warnings
- Markup application
- Labor calculations
- Detailed reporting

**SpecificationExtractor** - PDF processing
- Auto-detect insulation specs from PDFs
- Pattern matching for materials and thicknesses

**DrawingMeasurementExtractor** - Measurement processing
- Manual entry support
- Bulk CSV import
- Fitting calculations

**QuoteGenerator** - Professional outputs
- Formal quote generation
- Material list creation
- Alternative options pricing

---

## Configuration

### Environment Variables

Create `.env` file (optional):
```bash
DEFAULT_LABOR_RATE=65.0
DEFAULT_MARKUP=1.15
DEFAULT_CONTINGENCY=10
```

### Custom Styling

Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

---

## Pricing & Cost

### Streamlit Community Cloud
- **Free**: Unlimited public apps
- **Teams**: $250/month (private apps)

### Self-Hosted
- **AWS/GCP/Azure**: $20-50/month (small instance)
- **Heroku**: $7-25/month
- **Docker**: Pay for infrastructure only

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed cost breakdowns.

---

## Development

### Local Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run with auto-reload
streamlit run streamlit_app.py

# Run tests (if implemented)
pytest tests/
```

### Adding Features

1. Edit `streamlit_app.py` for UI changes
2. Edit `hvac_insulation_estimator.py` for calculation logic
3. Test locally
4. Commit and push
5. Auto-deploys on Streamlit Cloud

---

## Troubleshooting

### Common Issues

**App won't start**
```bash
# Check Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

**PDF extraction not working**
```bash
# Install pdfplumber
pip install pdfplumber
```

**Excel upload fails**
```bash
# Install openpyxl
pip install openpyxl
```

**Memory errors with large files**
- Reduce file sizes
- Split into smaller batches
- Increase server resources

---

## Roadmap

### Planned Features
- [ ] User authentication
- [ ] Project saving/loading
- [ ] Database integration
- [ ] Multi-project comparison
- [ ] Historical pricing trends
- [ ] Mobile app version
- [ ] API access
- [ ] Team collaboration
- [ ] Custom branding

### Integration Ideas
- [ ] QuickBooks integration
- [ ] Procore integration
- [ ] Email quote delivery
- [ ] SMS notifications
- [ ] Calendar scheduling

---

## Support

### Documentation
- [Deployment Guide](DEPLOYMENT.md)
- [Streamlit Docs](https://docs.streamlit.io)

### Community
- GitHub Issues: [Report bugs](https://github.com/glmoss-collab/PROINSULATIONESTIMATION/issues)
- Discussions: [Feature requests](https://github.com/glmoss-collab/PROINSULATIONESTIMATION/discussions)

### Commercial Support
For enterprise deployments, custom features, or training:
- Email: [your-email@example.com]
- Website: [your-website.com]

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License - See LICENSE file for details

---

## Credits

Built with:
- [Streamlit](https://streamlit.io) - Web framework
- [Pandas](https://pandas.pydata.org) - Data manipulation
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF extraction
- [OpenPyXL](https://openpyxl.readthedocs.io) - Excel support

---

## Screenshots

*Coming Soon*

---

**Ready to estimate? Deploy in 5 minutes with Streamlit Cloud!**

```bash
streamlit run streamlit_app.py
```
