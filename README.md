# dap-property

### NOTE
The tricky-alert folder located in ```/src/tricky-alert``` is temporary, and will have to 
be removed when that package is published on Pypi to be properly installed.

#### Running in Production:
```
#!/bin/bash

export REALTY_IN_US_HOST="TEST"
export REALTY_IN_US_KEY="TEST"
export US_REAL_ESTATE_HOST="TEST"
export US_REAL_ESTATE_KEY="TEST"
export MORTGAGE_CALCULATOR_URL="TEST"
export ZILLOW_URL="TEST"
export RECEIVER_EMAILS="LIST"
export SENDER_EMAIL="TEST"
export SENDER_PASS="TEST"
export LAST_RUN="THIS WILL READ FROM APP DATA"
export APP_DATA_PATH="PATH TO APP DATA"
export LOG_FILE="PATH TO LOG FILE"

source ./venv/bin/activate
cd ../src
python run.py
```