<template>
    <div class="navigation-wrapper">
        <img class="background-shape"  src="../../assets/bg-shape.svg"/>
        <div class="navigation">
            <b-navbar toggleable="lg">
                <!-- Light aligned nav items -->
                <b-navbar-brand class="ml-5">
                    <img class="licx-logo" src="../../assets/LICX-logo.svg" alt="logo"/>
                </b-navbar-brand>
                <!-- Right aligned nav items -->
                <b-navbar-nav v-if="wallet == null" class="ml-auto mr-5">
                    <b-nav-form>
                        <b-button class="btn-wallet"
                                  v-on:click="hasAccount">Connect Wallet</b-button>
                    </b-nav-form>
                </b-navbar-nav>
                <b-navbar-nav v-else class="ml-auto mr-5">
                    <b-nav-item class="walled-address" disabled>
                        {{wallet}}
                    </b-nav-item>
                    <b-nav-form>
                        <b-button class="btn-wallet"
                                  v-on:click="setWallet(null)">Log out</b-button>
                    </b-nav-form>
                </b-navbar-nav>
            </b-navbar>
        </div>
    </div>
</template>


<style lang="sccs" scoped src="./header.scss"></style>
<script lang="ts" src="./header.ts"></script>
