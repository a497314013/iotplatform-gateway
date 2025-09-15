

set -e # exit on any error

# Fetch the current branch name and latest commit ID
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD | sed 's/[\/]/-/g')
COMMIT_ID=$(git rev-parse --short HEAD)

# Combine them to create a version tag
VERSION_TAG="${BRANCH_NAME}-${COMMIT_ID}"

echo "$(date) Building project with version tag $VERSION_TAG ..."
set -x

# multi arch
 DOCKER_CLI_EXPERIMENTAL=enabled \
 docker buildx build . -t tb-gateway:$VERSION_TAG -f docker/Dockerfile --platform=linux/amd64,linux/arm64 -o type=registry

set +x
echo "$(date) Done."
