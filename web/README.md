# Liquid ICX frontend 🧽💧

This README guides you through running the frontend yourself.

## Requirements without Docker
* Node (to run without docker)
* Npm (to run without docker)
* Docker (to run with docker)

## Quickstart

Install docker and run our public docker image:
```
docker run -p 8080:3000 -d block42blockchaincompany/liquid-icx-frontend:latest
```

## Run VueJs 

Install the Requirements as described above.
Open the web/ directory in your terminal and install the dependencies via:
```
npm install
```

Next run the VueJs development server with:
```
npm run serve
```

The output of the `npm run serve` command shows you the URL through which
you can access the website in your browser, 
in our case it shows `http://localhost:8080/`.

## VueJs Production Build

To minify the code to use it for production, run:
```
npm run build
```

This minifies the whole project and puts it in the `dist/` folder.

You can now copy the `dist/` folder to your web hosting directory.
On many web servers (Apache, Nginx) this is the `/var/www/html/` folder.

So go ahead, put `dist/` inside `/var/www/html/` of your local/remote machine
and you can access the website on this machine.

## VueJs commands:

Project setup
```
npm install
```

Compiles and hot-reloads for development
```
npm run serve
```

Compiles and minifies for production
```
npm run build
```

Run your unit tests
```
npm run test:unit
```

Lints and fixes files
```
npm run lint
```

To customize configuration see [Configuration Reference](https://cli.vuejs.org/config/).
