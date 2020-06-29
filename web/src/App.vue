<template>
  <div id="licx-app">
    <div id="main-content">
      <Header />
      <router-view/>
    </div>
    <Footer />
  </div>
</template>

<script>
import Component from 'vue-class-component'
import {Vue} from "vue-property-decorator";
import Header from '@/components/header/Header.vue'
import Footer from '@/components/footer/Footer.vue'

@Component({
components: {
  Header,
    Footer
}
})

export default class Home extends Vue {

}
</script>

<style lang="scss">
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@200;300;400;500;600;700&display=swap');



body{
  margin: 0;
  #licx-app {
    /*Base styling*/
    position: relative;
    font-family: 'Open Sans', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-align: center;
    color: #1BAABA;
    min-height: 100vh;
    #main-content{
      padding-bottom: 2.5rem;
    }
    /* Base input class */
    .input-licx {
      border: none;
      border-bottom: 2px solid $background-base-washed;
      text-align: center;
      font-size: 1.5em;
      @media (min-width: 300px) and (max-width: 600px) {
        font-size: 1em;
      }
    }

    /* Base btn class */
    .btn-licx {
      border: none;
      border-radius: 0;
      font-size: 1.3em;
      background: $icx-base;
      font-weight: 600;
      &:disabled{
        cursor: not-allowed;
        pointer-events: all !important;
      }
    }

    /* Base media mobile class*/
    @media (min-width: 300px) and (max-width: 600px) {
      font-size: .7em;
    }
  }
}
</style>
