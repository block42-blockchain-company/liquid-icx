<template>
  <div class="home">
      <Header />

      <div class="main-content container-fluid" style="width: 70%">
          <div class="row">
              <div class="col-sm-7">
                  <Swap />
              </div>
              <div class="offset-sm-1 col-sm-4">
                  <Balance />
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
import Balance from "@/components/balance/Balance.vue";


@Component({
  components: {
    Header,
    Swap,
    Balance
  }
})

export default class Home extends Vue {
  
}
</script>
