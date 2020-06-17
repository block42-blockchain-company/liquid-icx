<template>
  <div id="app">
    <router-view/>
  </div>
</template>

<style lang="scss">
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@200;300;400;500;600;700&display=swap');



body{
  margin: 0;
  #app {
    /*Base styling*/
    font-family: 'Open Sans', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-align: center;
    color: #1BAABA;

    /* Base input class*/
    .input-licx {
      border: none;
      border-bottom: 2px solid $background-base-washed;
      text-align: center;
      font-size: 1.5em;
    }

    /*Base btn class*/
    .btn-licx {
      border: none;
      border-radius: 0;
      font-size: 1.3em;
      background: $icx-base;
      &:disabled{
        cursor: not-allowed;
        pointer-events: all !important;
      }
    }

  }
}
</style>
