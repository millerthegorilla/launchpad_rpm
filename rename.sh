git filter-branch --env-filter 'if [ "$GIT_AUTHOR_EMAIL" = "james@localhost" ]; then
     GIT_AUTHOR_EMAIL=jamesstewartmiller@gmail.com;
     GIT_AUTHOR_NAME="james miller";
     GIT_COMMITTER_EMAIL=$GIT_AUTHOR_EMAIL;
     GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"; fi' -- --all
