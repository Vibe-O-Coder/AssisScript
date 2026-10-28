/* Induction proofs with mathematical (nonwrapping) interval endpoints. Calls
 * are allowed only with the checked scalar pure contract. No alias/mutation
 * or speculative hoisting is permitted across the collection identity. */
static bool range_stable(Node *n,Var *index,Var *buffer){
    if(!n)return true;
    if(n->kind==N_CALL&&(!n->fn||!n->fn->pure||n->fn->owner))return false;
    if(n->kind==N_NEW||n->kind==N_FREE||n->kind==N_DEFER||n->kind==N_UNSAFE||n->kind==N_ARRAY)return false;
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
static bool range_index(Node *n,Var *index,int64_t low,int64_t upper_offset){
    int64_t offset=0;Node *base=n;uint64_t value;
    if(n->kind==N_BINARY&&(n->op=='+'||n->op=='-')&&equal_type(n->ty,type_i64)&&constant(n->b,&value)){
        /* Exclude INT64_MIN so negation and endpoint arithmetic stay defined. */
        if(value==UINT64_C(0x8000000000000000))return false;
        offset=n->op=='+'?(int64_t)value:-(int64_t)value;base=n->a;
    }
    if(base->kind!=N_NAME||base->var!=index)return false;
    /* i is in [low, len(buffer)-1-upper_offset]. Offsets must keep both
     * endpoints within [0,len(buffer)-1], including an empty iteration set. */
    return offset>=-low&&offset<=upper_offset;
}
static void range_mark(Node *n,Var *index,Var *buffer,int64_t low,int64_t upper_offset){
    if(!n)return;
    if(n->kind==N_INDEX&&n->a->kind==N_NAME&&n->a->var==buffer&&range_index(n->b,index,low,upper_offset))n->bounds_proven=true;
    range_mark(n->a,index,buffer,low,upper_offset);range_mark(n->b,index,buffer,low,upper_offset);range_mark(n->c,index,buffer,low,upper_offset);range_mark(n->step,index,buffer,low,upper_offset);
    for(int i=0;i<n->items.n;i++)range_mark(n->items.v[i],index,buffer,low,upper_offset);
}
static Node *range_length(Node *n,int64_t *offset){
    uint64_t value;*offset=0;
    if(n->kind==N_BINARY&&n->op=='-'&&equal_type(n->ty,type_i64)&&constant(n->b,&value)){
        if(value>INT64_MAX)return NULL;*offset=(int64_t)value;n=n->a;
    }
    return n->kind==N_BUILTIN&&n->op==T_LEN?n->items.v[0]:NULL;
}
static void range_pair(Node *init,Node *loop){
    uint64_t start,step_value;
    if(init->kind!=N_LET||!equal_type(init->decl,type_i64)||init->var->address_taken)return;
    if(loop->kind!=N_WHILE||!loop->step)return;
    Node *test=loop->a,*step=loop->step;
    if(test->kind!=N_BINARY||test->a->kind!=N_NAME||test->a->var!=init->var)return;
    if(step->kind!=N_ASSIGN||step->a->kind!=N_NAME||step->a->var!=init->var||!constant(step->b,&step_value))return;
    Node *array=NULL;int64_t low=0,upper=0;
    if(test->op=='<'&&step->op==T_ADDSET&&step_value==1&&constant(init->a,&start)&&start<=INT64_MAX){
        low=(int64_t)start;array=range_length(test->b,&upper);
    }
    else if(test->op==T_GE&&step->op==T_SUBSET&&step_value==1&&constant(test->b,&start)&&start<=INT64_MAX){
        low=(int64_t)start;array=range_length(init->a,&upper);if(upper<1)return;upper--;
    }
    else return;
    if(!array)return;
    if(array->kind!=N_NAME||!array->ownership||array->var->address_taken||(!array->ty.depth&&!slice_type(array->ty)&&!collection_of(array->ty)))return;
    if(range_stable(loop->b,init->var,array->var))range_mark(loop->b,init->var,array->var,low,upper);
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
