import {Component , Mixins} from 'vue-property-decorator'
import {IconMixin} from "@/mixins/IconMixin";
import {mapGetters} from "vuex";
import {reflectionIsSupported} from "vue-class-component/lib/reflect";


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

        this.getLicxApi().then(result => console.log(result))

        this.buildTransaction({
            write: true,
            method: "join",
            from: this.wallet.address,
            params: {},
            value: Number(this.amount)
        }).then(result => {
            console.log(result)
        })
    }
}