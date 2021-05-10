# Generate virtualenv
init:
	pip install --upgrade pip pipenv
	pipenv install

# Config pipenv
config:
	pipenv --rm || true && \
	pipenv sync

# Download ansible roles
update-roles:
	@pipenv run ansible-galaxy install -r requirements.yml --force

# Check syntax and inventory
tests:
	@pipenv run ansible-playbook -i hosts.yml playbook.yml --syntax-check
	@pipenv run ansible-inventory -i hosts.yml --graph -y
	@pipenv run ansible-playbook -i hosts.yml playbook.yml --list-hosts
	
# Check playbook execution
plan:
	@pipenv run ansible-playbook -i hosts.yml playbook.yml --check $(args)

# Provision
apply:
	@pipenv run ansible-playbook -i hosts.yml playbook.yml $(args)
