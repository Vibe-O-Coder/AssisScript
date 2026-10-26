/* Conservative induction proof for `for (let i:int=0; i<len(a); i+=1)`.
 * All semantic passes run first. Reject calls, raw operations and every write
 * to the induction variable or collection identity. No speculative hoisting. */
static bool range_stable(Node *n,Var *index,Var *buffer){
    if(!n)return true;
    if(n->kind==N_CALL||n->kind==N_NEW||n->kind==N_FREE||n->kind==N_DEFER||n->kind==N_UNSAFE||n->kind==N_ARRAY)return false;
    if(n->kind==N_UNARY&&(n->op=='&'||n->op=='*'))return false;
    if(n->kind==N_BINARY&&n->ty.depth)return false;
    if(n->kind==N_LET&&resource_type(n->decl))return false;
    if(n->kind==N_INDEX&&n->a->ty.depth&&!n->a->ownership)return false;
    if(n->kind==N_ASSIGN&&n->a->kind==N_NAME&&(n->a->var==index||n->a->var==buffer))return false;
    if(n->kind==N_BUILTIN&&n->op!=T_LEN&&n->op!=T_ASSERT&&n->op!=T_I64&&n->op!=T_U8&&n->op!=T_BOOL&&n->op!=T_NUMTYPE)return false;
    if(!range_stable(n->a,index,buffer)||!range_stable(n->b,index,buffer)||!range_stable(n->c,index,buffer)||!range_stable(n->step,index,buffer))return false;
    for(int i=0;i<n->items.n;i++)if(!range_stable(n->items.v[i],index,buffer))return false;
    return true;
}
static void range_mark(Node *n,Var *index,Var *buffer){
    if(!n)return;
    if(n->kind==N_INDEX&&n->a->kind==N_NAME&&n->a->var==buffer&&n->b->kind==N_NAME&&n->b->var==index)n->bounds_proven=true;
    range_mark(n->a,index,buffer);range_mark(n->b,index,buffer);range_mark(n->c,index,buffer);range_mark(n->step,index,buffer);
    for(int i=0;i<n->items.n;i++)range_mark(n->items.v[i],index,buffer);
}
static void range_pair(Node *init,Node *loop){
    uint64_t zero,one;
    if(init->kind!=N_LET||!equal_type(init->decl,type_i64)||!constant(init->a,&zero)||zero||init->var->address_taken)return;
    if(loop->kind!=N_WHILE||!loop->step)return;
    Node *test=loop->a,*step=loop->step;
    if(test->kind!=N_BINARY||test->op!='<'||test->a->kind!=N_NAME||test->a->var!=init->var||test->b->kind!=N_BUILTIN||test->b->op!=T_LEN)return;
    Node *array=test->b->items.v[0];
    if(array->kind!=N_NAME||!array->ownership||array->var->address_taken||(!array->ty.depth&&!slice_type(array->ty)&&!collection_of(array->ty)))return;
    if(step->kind!=N_ASSIGN||step->op!=T_ADDSET||step->a->kind!=N_NAME||step->a->var!=init->var||!constant(step->b,&one)||one!=1)return;
    if(range_stable(loop->b,init->var,array->var))range_mark(loop->b,init->var,array->var);
}
static void range_walk(Node *n){
    if(!n)return;
    if(n->kind==N_BLOCK)for(int i=1;i<n->items.n;i++)range_pair(n->items.v[i-1],n->items.v[i]);
    range_walk(n->a);range_walk(n->b);range_walk(n->c);range_walk(n->step);
    for(int i=0;i<n->items.n;i++)range_walk(n->items.v[i]);
}
static void prepare_ranges(void){for(int i=0;i<all_functions.n;i++)range_walk(((Function*)all_functions.v[i])->body);}
static int range_count(Node *n){
    if(!n)return 0;int count=n->bounds_proven?1:0;
    count+=range_count(n->a)+range_count(n->b)+range_count(n->c)+range_count(n->step);
    for(int i=0;i<n->items.n;i++)count+=range_count(n->items.v[i]);return count;
}
