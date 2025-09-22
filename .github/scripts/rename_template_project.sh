#!/usr/bin/env bash
while getopts a:n:u:d: flag
do
    case "${flag}" in
        a) author=${OPTARG};;
        n) name=${OPTARG};;
        u) urlname=${OPTARG};;
        d) description=${OPTARG};;
    esac
done

echo "Author: $author";
echo "Project Name: $name";
echo "Description: $description";

echo "Renaming project..."

original_author="author_name"
original_name="ukr_energy_dash"
original_description="project_description"
# for filename in $(find . -name "*.*")
for filename in $(git ls-files)
do
    # Skip certain files
    if [[ $filename =~ ^\.github/(rulesets|scripts|workflows)/ ]]; then
        echo "Skipping $filename"
        continue
    fi

    # Perform replacements
    sed -i "s/$original_author/$author/g" $filename
    sed -i "s/$original_name/$name/g" $filename
    sed -i "s/$original_description/$description/g" $filename

    # Check if changes were made to the file
    if [[ $(git diff --quiet $filename; echo $?) != 0 ]]; then
        echo "Renamed contents in $filename"
    else
        echo "Reviewed contents in $filename, no changes made."
    fi
done

echo "Renaming file names..."

mv src/ukr_energy_dash src/$name
echo "Renamed src/ukr_energy_dash to src/$name"

mv notebooks/sample_ukr_energy_dash.ipynb notebooks/sample_$name.ipynb
echo "Renamed notebooks/sample_ukr_energy_dash.ipynb to notebooks/sample_$name.ipynb"

mv tests/test_ukr_energy_dash.py tests/test_$name.py
echo "Renamed tests/test_ukr_energy_dash.py to tests/test_$name.py"

# This command runs only once on GHA!
rm -rf .github/template.yml
echo "Deleted .github/template.yml"
