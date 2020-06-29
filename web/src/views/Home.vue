<template>
  <div class="home">
      <Header />
      <div class="main-content container-fluid">
          <div class="row d-flex justify-content-between">
              <div class="col-lg-8 p-0">
                  <Swap />
              </div>
              <div class="col-lg-4 p-0">
                  <Balance />
              </div>
          </div>
          <div class="row d-flex justify-content-between">
              <div class="col-sm-12 p-0 mt-5">
                  <Transfer />
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
import Transfer from "@/components/transfer/Transfer.vue";


@Component({
  components: {
    Header,
    Swap,
    Balance,
    Transfer
  }
})

export default class Home extends Vue {
  
}
</script>

<style lang="scss">
    .main-content{
        width: 65% !important;
    }
</style>
