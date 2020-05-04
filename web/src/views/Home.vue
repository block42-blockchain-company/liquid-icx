<template>
  <div class="home">
    <Header />
    wadup boy
  </div>
</template>

<script>
// @ is an alias to /src
import Vue from 'vue'
import Component from 'vue-class-component'

import Header from '@/components/header/Header.vue'

import IconService from 'icon-sdk-js'

@Component({
  components: {
    Header,
    IconService
  }
})
export default class Home extends Vue {
  created(){
    const provider = new IconService.HttpProvider('https://bicon.net.solidwallet.io/api/v3');
    const iconService = new IconService(provider);
    //console.log(provider);
    
    
    //const { IconWallet } = IconService;
    //#const wallet = IconWallet.create()
    //console.log(wallet.getAddress());
    
    
  }
  
}
</script>
