<template>
    <b-navbar-nav v-if="wallet == null" class="ml-auto mr-5">
        <b-nav-form>
            <b-button class="btn-wallet"
                      v-on:click="hasAccount">Connect Wallet</b-button>
        </b-nav-form>
    </b-navbar-nav>

    <b-navbar-nav v-else class="ml-auto mr-5">
        <b-nav-item class="wallet-address" disabled>
            {{wallet.address}}
        </b-nav-item>
        <b-nav-form>
            <b-button class="btn-wallet"
                      v-on:click="setWallet(null)">Log out</b-button>
        </b-nav-form>
    </b-navbar-nav>
</template>

<style lang="sccs" scoped src="./iconWallet.scss"></style>
<script lang="ts" src="./iconWallet.ts"></script>
