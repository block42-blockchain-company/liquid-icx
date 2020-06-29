<template>
    <div class="navigation-wrapper">
        <img href="" class="background-shape"  src="../../assets/bg-shape.svg"/>
        <div class="navigation">
            <b-navbar toggleable="lg">
                <!-- Left aligned nav items -->
                <b-navbar-brand class="ml-5">
                    <router-link to="/">
                        <img class="licx-logo" src="../../assets/LICX-logo.svg" alt="logo"/>
                    </router-link>
                </b-navbar-brand>
                <!-- Right aligned nav items -->
                <IconWallet></IconWallet>
            </b-navbar>
        </div>
    </div>
</template>


<style lang="sccs" scoped src="./header.scss"></style>
<script lang="ts" src="./header.ts"></script>
