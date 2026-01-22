FROM postgres:13

ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword 
ENV POSTGRES_DB=storedb 

COPY sql/init.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
