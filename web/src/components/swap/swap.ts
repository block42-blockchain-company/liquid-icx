import {Component , Mixins} from 'vue-property-decorator'
import {IconMixin} from "@/mixins/IconMixin";
import {mapGetters} from "vuex";
import {IconConverter, IconAmount} from 'icon-sdk-js'

@Component({
    components: {},
    computed: mapGetters({ wallet : 'getWallet'}),
})
export default class Swap extends Mixins(IconMixin) {

    wallet !: Record<string, any> | null

    readonly pairs = {
        "LICX": "ICX",
        "ICX": "LICX"
    };


    amount = "";

    join() {
        if(!this.wallet) return;
        if(this.wallet.icxBalance == 0){
            alert("Buy some icx first");
            return;
        }

        const tx = this.buildTransaction({
            write: true,
            method: "join",
            steps: 200000,
            from: this.wallet.address,
            params: {},
            value: IconAmount.of(this.amount, IconAmount.Unit.ICX).convertUnit(IconAmount.Unit.LOOP)
        })

        window.dispatchEvent(new CustomEvent('ICONEX_RELAY_REQUEST', {
            detail: {
                type: 'REQUEST_JSON-RPC',
                payload: {
                    jsonrpc: "2.0",
                    method: "icx_sendTransaction",
                    params: IconConverter.toRawTransaction(tx),
                    id: 50889
                }
            }
        }));

        //this.getBalances(this.wallet.address)
    }
}
