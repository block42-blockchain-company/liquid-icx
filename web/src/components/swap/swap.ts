import {Component , Mixins} from 'vue-property-decorator'
import {IconMixin} from "@/mixins/IconMixin";
import {mapGetters} from "vuex";


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
            from: this.wallet.address,
            params: {},
            value: Number(this.amount)
        })

    }
}
