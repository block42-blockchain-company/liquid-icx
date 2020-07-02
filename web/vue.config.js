module.exports = {
    css: {
        loaderOptions: {
            sass: {
                prependData: `@import "@/styles/variables.scss";`
            }
        }
    },
    outputDir: "deploy/dist"
};