#! /bin/sh

cp='cp -vi'
do_force=false
if [ "$1" = "--force" ] ; then
    shift
    do_force=true
    cp="${cp//i/}"
fi

echo "adding git hook templates"
git config --global init.templatedir '~/.git-templates'
mkdir -p ~/.git-templates/hooks
$cp bin/hooks/* ~/.git-templates/hooks
hook_files="$(find bin/hooks -type f -exec basename {} \;)"
chmod u+x ~/.git-templates/hooks
for git_dir in $(find .. -name .git); do
    repo="${git_dir%/.git}"
    if [ -d "$repo" ]; then
        cd $repo
        if $do_force ; then
            for file in $hook_files; do
                rm .git/hooks/$file
            done
        fi
        git init
    fi
done
