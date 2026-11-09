#!/bin/sh
# Copies skills/comfyui-workflow into ~/.claude/skills and, if ~/.codex exists,
# into ~/.codex/skills. Only that one folder is replaced. Safe to run repeatedly.
set -eu

name=comfyui-workflow
repo_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
source_dir="$repo_dir/skills/$name"

if [ ! -d "$source_dir" ]; then
    echo "error: $source_dir not found" >&2
    exit 1
fi
if [ -z "${HOME:-}" ] || [ ! -d "$HOME" ]; then
    echo "error: HOME is not set to an existing folder" >&2
    exit 1
fi

staging=''
cleanup() {
    if [ -n "$staging" ]; then
        rm -rf -- "$staging"
    fi
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

install_to() {
    skills_dir=$1
    target="$skills_dir/$name"

    mkdir -p -- "$skills_dir"
    if [ -d "$target" ] && [ ! -L "$target" ] &&
        [ "$(CDPATH='' cd -- "$target" && pwd -P)" = "$source_dir" ]; then
        echo "unchanged: $target is the source folder itself"
        return 0
    fi

    # Copy first and swap last, so a failed copy leaves the old install intact.
    staging="$skills_dir/.$name.installing.$$"
    rm -rf -- "$staging"
    mkdir -- "$staging"
    cp -R -- "$source_dir/." "$staging/"
    find "$staging" \( -name .DS_Store -o -name __pycache__ \) -prune -exec rm -rf -- {} +
    printf '%s\n' "$repo_dir" > "$staging/REPO_PATH"

    if [ -e "$target" ] || [ -L "$target" ]; then
        action=replaced
        rm -rf -- "$target"
    else
        action=installed
    fi
    mv -- "$staging" "$target"
    staging=''

    count=$(find "$target" -type f | wc -l | tr -d ' ')
    echo "$action: $target ($count files)"
}

install_to "$HOME/.claude/skills"

if [ -d "$HOME/.codex" ]; then
    install_to "$HOME/.codex/skills"
else
    echo "skipped: $HOME/.codex does not exist"
fi
