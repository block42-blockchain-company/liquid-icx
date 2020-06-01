import {Component , Mixins} from 'vue-property-decorator'
import {IconMixin} from "@/mixins/IconMixin";
import {mapGetters} from "vuex";


@Component({
    components: {},
    computed: mapGetters({ wallet : 'getWallet'}),
})
export default class Balance extends Mixins(IconMixin) {
    wallet !: Record<string, any> | null

    getICX() {
        if (this.wallet) {
            return (this.wallet.balances.icx / BigInt (Math.pow(10, 18)))
        }
    }

    getLICX() {
        if (this.wallet) {
            return (this.wallet.balances.licx / BigInt (Math.pow(10, 18)))
        }
    }
}
