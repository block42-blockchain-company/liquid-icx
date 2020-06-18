import {Component , Mixins} from 'vue-property-decorator'
import {IconMixin} from "@/mixins/IconMixin";
import {mapGetters} from "vuex";
import {IconConverter, IconAmount} from 'icon-sdk-js'


@Component({
  components: {},
  computed: mapGetters({ wallet : 'getWallet'}),
})
export default class Transfer extends Mixins(IconMixin) {

  wallet !: Record<string, any> | null

  to_address: string | null = null

  to_amount: number | null = null

  transfer() {
    if(!this.wallet) return
    if(this.to_amount != null && this.to_amount <= 0) {
      alert("amount can't be zero or less")
      return
    }
    if(!this.checkAddress(this.to_address!)) {
      alert("invalid address")
      return;
    }

    window.dispatchEvent(new CustomEvent('ICONEX_RELAY_REQUEST', {
      detail: {
        type: 'REQUEST_JSON-RPC',
        payload: {
          jsonrpc: "2.0",
          method: "icx_sendTransaction",
          params: IconConverter.toRawTransaction(this.buildTransaction({
            write: true,
            method: "transfer",
            steps: 200000,
            from: this.wallet.address,
            params: {"_to": this.to_address,
              "_value": IconConverter.toHex(IconAmount.of(this.to_amount, IconAmount.Unit.ICX).toLoop())},
          })),
          id: 50889
        }
      }
    }));
  }
}
