<template>
  <div class="home">
      <Header />

      <div class="main-content container-fluid" style="width: 70%">
          <div class="row">
              <div class="col-sm-7">
                  <Swap />
              </div>
          </div>
      </div>
  </div>
</template>


<script>
// @ is an alias to /src
//import Vue from 'vue'
import Component from 'vue-class-component'
import {Vue} from "vue-property-decorator";
import Header from '@/components/header/Header.vue'
import Swap from "@/components/swap/Swap.vue";

import IconService from 'icon-sdk-js'

@Component({
  components: {
    Header,
    IconService,
    Swap
  }
})

export default class Home extends Vue {
  
}
</script>
