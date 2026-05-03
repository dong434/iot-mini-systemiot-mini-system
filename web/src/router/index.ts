//创建第一个路由器，并暴露出去

//第一步:引入CreateRouter和组件
import {createRouter,createWebHistory} from 'vue-router'
import login from "../components/login.vue"
import dashboard from "../components/dashboard.vue"
//第二步:创建路由器
const router=createRouter({
    history:createWebHistory(),
    routes:[
        {
          path:"/",
          redirect:"/login",
        },
        {
            path:'/login',
            name:'登录',
            component:login,
            // children:[       适用前提是把子页面的vue导进来
            //     {
            //         path:"子集地址",   地址不用加/
            //     }
            // ]
        },
        {
            path:'/dashboard',
            name:'实时数据',
            component:dashboard
        }
    ]
}
)
router.beforeEach((to, from) => {
    if(to.path==='/dashboard' && !sessionStorage.getItem('token')){
        alert("请先登录")
        return '/login'
    }
    else{
        return true;
    }
})
export default router