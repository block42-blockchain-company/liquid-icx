import { Mixins, Component } from 'vue-property-decorator'
import {mapGetters, mapMutations} from "vuex";
import store from "@/store";
import {IconMixin} from "@/mixins/IconMixin";

@Component({
})
export default class IconWallet extends Mixins(IconMixin)
{
}
