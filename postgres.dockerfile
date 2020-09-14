FROM postgres:12

LABEL project="series"

WORKDIR /usr/share/postgresql/12/

COPY series/postgres_extra_files/extensions/hunspell/extension/      /usr/share/postgresql/12/extension/
COPY series/postgres_extra_files/extensions/hunspell/tsearch_data/   /usr/share/postgresql/12/tsearch_data/