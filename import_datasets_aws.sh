#!/bin/bash

SOURCE_BUCKET="s3://lithops-applications-data"
# We do not allow listing objects for security
AIRBNB_OBJECTS=(
"Amsterdam-2024-09-06-reviews.csv"
"Barcelona-2024-09-11-reviews.csv" 
"Berlin-2024-09-28-reviews.csv" 
"Montreal-2024-09-13-reviews.csv" 
"Portland-2024-09-05-reviews.csv"
)
GROMACS_OBJECTS=("benchMEM.zip")
PUBLIC_OBJECTS=("${AIRBNB_OBJECTS[@]}" "${GROMACS_OBJECTS[@]}")
echo "Public objects to be copied:"
for OBJECT in "${PUBLIC_OBJECTS[@]}"; do
    echo "$OBJECT"
done

if [ -z "$1" ]; then
    echo "Usage: $0 <destination_bucket>"
    exit 1
fi

DESTINATION_BUCKET=$1

echo "The requesting client will pay for the data transfer. Do you want to continue? [Y/n]"
read -r response
if [[ "$response" != "Y" && "$response" != "y" && "$response" != "" ]]; then
    echo "Operation aborted."
    exit 1
fi

for OBJECT in "${PUBLIC_OBJECTS[@]}"; do
    aws s3 cp "$SOURCE_BUCKET/$OBJECT" "$DESTINATION_BUCKET/$OBJECT" --request-payer requester
done