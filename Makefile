.PHONY: release
release:
	@git flow release finish `git flow release | cut -d ' ' -f2`
	@git push --all
	@git push --tags
	@git checkout develop
