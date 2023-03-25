extract: # Extract strings from code to .POT file
	poetry run -- python -m cli extract

update: # Update .PO file for Russian language
	poetry run -- python -m cli update -l ru

full_update: # Extract strings and update .PO file for Russian language
	poetry run -- python -m cli full_update -l ru

compile: # Compile .PO files to .MO files
	poetry run -- python -m cli compile
