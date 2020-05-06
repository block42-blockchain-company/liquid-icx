<template>
  <div class="home">
      <Header />
  </div>
</template>


<script>
// @ is an alias to /src
//import Vue from 'vue'
import Component from 'vue-class-component'
import {Vue} from "vue-property-decorator";

import Header from '@/components/header/Header.vue'

import IconService from 'icon-sdk-js'

@Component({
  components: {
    Header,
    IconService
  }
})

export default class Home extends Vue {
  
}
</script>
