
### Usage
docker build -t gp2mb --build-arg BASE_IMAGE=$BASE_IMAGE .

docker run -it -e GS_SECRET_ACCESS_KEY=7oipOqgMC2b7NFI37aOJVEvUwb8/84cggjebB73U -e GS_ACCESS_KEY_ID=GOOG1EAWTN2EVMJWVO3ES5DLNZ6JKJ3KGK5X7ID7WXN7CVKDL47ST37B5RKT7 -v $PWD:/app --entrypoint bash -p 8080:8080 gp2mb
