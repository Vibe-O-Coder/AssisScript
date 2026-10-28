/* Standalone developer commands; never execute compiler helpers. */
static int format_command(int argc,char **argv){
    const char *input="assis.assis";bool checking_format=false,has_input=false;
    for(int i=2;i<argc;i++){if(same(argv[i],"--check"))checking_format=true;else if(argv[i][0]=='-')fatal("opção de fmt desconhecida: %s",argv[i]);else if(!has_input){input=argv[i];has_input=true;}else fatal("fmt recebe um arquivo");}
    SourceFile *file=mem(sizeof(*file));file->path=absolute_path(input);file->text=read_module_text(file->path,false);push(&source_files,file);current_source=file;filename=file->path;source=file->text;lex();
    size_t capacity=strlen(source)*2+1024,used=0;char *out=mem(capacity);const char *line=source;int number=1,depth=0,index=0;
    while(*line){
        const char *end=strchr(line,'\n');if(!end)end=line+strlen(line);const char *a=line,*b=end;
        while(a<b&&(*a==' '||*a=='\t'||*a=='\r'))a++;while(b>a&&(b[-1]==' '||b[-1]=='\t'||b[-1]=='\r'))b--;
        int leading=0,j=index;bool only_close=true;
        while(j<tokens.n){Token *t=tokens.v[j];if(t->kind==T_EOF||t->line>number)break;if(t->line==number){if(t->kind=='}'&&only_close)leading++;else only_close=false;}j++;}
        int indent=depth-leading;if(indent<0)indent=0;if(indent>MAX_NEST)fatal("fmt: profundidade de blocos excedida");
        size_t needed=used+(size_t)indent*4+(size_t)(b-a)+2;
        if(needed>MAX_SOURCE*4u)fatal("fmt: saída excessiva");if(needed>capacity){capacity=needed*2;out=realloc(out,capacity);if(!out)fatal("memória insuficiente");}
        if(a<b){memset(out+used,' ',(size_t)indent*4);used+=(size_t)indent*4;memcpy(out+used,a,(size_t)(b-a));used+=(size_t)(b-a);}out[used++]='\n';
        for(;index<j;index++){Token *t=tokens.v[index];if(t->kind=='{')depth++;else if(t->kind=='}')depth--;if(depth<0)error(t,"fmt encontrou fechamento de bloco sem abertura");}
        if(!*end)break;line=end+1;number++;
    }
    out[used]=0;if(depth)fatal("fmt encontrou bloco sem fechamento");bool changed=!same(source,out);
    if(checking_format){if(changed){fprintf(stderr,"class: %s precisa de formatação.\n",input);return 1;}return 0;}
    if(changed){
        char *temporary=mem(strlen(file->path)+64);FILE *f=NULL;
        for(unsigned i=0;i<100&&!f;i++){snprintf(temporary,strlen(file->path)+64,"%s.fmt.%lu.%u",file->path,(unsigned long)time(NULL),i);f=fopen(temporary,"wbx");}
        if(!f)fatal("fmt não conseguiu criar arquivo temporário");bool ok=fwrite(out,1,used,f)==used;if(fclose(f))ok=false;
#ifdef _WIN32
        if(ok){wchar_t *a=wide_path(temporary),*b=wide_path(file->path);ok=MoveFileExW(a,b,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;free(a);free(b);}
#else
        struct stat st;if(ok&&(!stat(file->path,&st)))ok=chmod(temporary,st.st_mode&0777)==0;
        if(ok)ok=rename(temporary,file->path)==0;
#endif
        if(!ok){unlink(temporary);fatal("fmt não conseguiu substituir o arquivo");}free(temporary);
    }
    printf("class: %s %s.\n",input,changed?"formatado":"já formatado");return 0;
}
static Function *test_driver;
static bool test_name(const char *name){const char *p=name;for(const char *c=name;*c;c++)if(c[0]==':'&&c[1]==':')p=c+2;return !strncmp(p,"test_",5)||!strncmp(p,"teste_",6);}
static void prepare_tests(void){
    SourceFile *root=source_files.v[0];Token *site=mem(sizeof(*site));site->file=root;site->at=root->text;site->line=1;site->col=1;site->text="__assis_tests";
    Function *driver=mem(sizeof(*driver));driver->t=site;driver->id=++next_definition;driver->safe=true;driver->result=type_i64;driver->body=node(N_BLOCK,site);int count=0;
    for(int i=0;i<generic_functions.n;i++){Function *f=generic_functions.v[i];if(f->t->file==root&&test_name(f->t->text))error(f->t,"teste não pode ser genérico");}
    for(int i=0;i<functions.n;i++){
        Function *f=functions.v[i];if(f->t->file!=root||!test_name(f->t->text))continue;
        if(f->params.n||f->result_mode||(!equal_type(f->result,type_void)&&!equal_type(f->result,type_i64)&&!equal_type(f->result,type_bool)))error(f->t,"teste exige zero parâmetros e retorno void, int (0 passa) ou bool (true passa)");
        driver->safe=driver->safe&&(f->safe||f->pure);Node *call=node(N_CALL,f->t);call->a=node(N_NAME,f->t);Node *statement=node(N_EXPR,f->t);
        if(equal_type(f->result,type_void))statement->a=call;
        else{Node *assertion=node(N_BUILTIN,f->t);assertion->op=T_ASSERT;Node *condition=call;
            if(equal_type(f->result,type_i64)){condition=node(N_BINARY,f->t);condition->op=T_EQ;condition->a=call;Token *zero=mem(sizeof(*zero));*zero=*f->t;zero->number=0;zero->kind=T_INT;condition->b=node(N_INT,zero);}push(&assertion->items,condition);statement->a=assertion;}
        push(&driver->body->items,statement);count++;
    }
    if(!count)error(site,"nenhum teste: declare fn test_nome(): void/int/bool");
    Node *print=node(N_PRINT,site);Token *message=mem(sizeof(*message));*message=*site;char text[80];snprintf(text,sizeof(text),"ASSIS: %d testes passaram",count);message->str=copy(text,strlen(text));message->len=strlen(text);push(&print->items,node(N_STR,message));push(&driver->body->items,print);
    Node *ret=node(N_RETURN,site);Token *zero=mem(sizeof(*zero));*zero=*site;zero->kind=T_INT;ret->a=node(N_INT,zero);push(&driver->body->items,ret);
    test_driver=driver;push(&functions,driver);push(&all_functions,driver);
}
static bool documented_symbol(Token *t){
    if(t->file!=source_files.v[0])return false;
    for(int i=0;i<module_symbols.n;i++){ModuleSymbol *s=module_symbols.v[i];if(s->token==t)return s->exported;}return true;
}
static void doc_comment(FILE *out,Token *t){
    const char *begin=t->at;while(begin>t->file->text&&begin[-1]!='\n')begin--;const char *first=begin;
    while(first>t->file->text){const char *end=first-1,*line=end;while(line>t->file->text&&line[-1]!='\n')line--;const char *p=line;while(p<end&&(*p==' '||*p=='\t'))p++;if(strncmp(p,"///",3))break;first=line;}
    for(const char *line=first;line<begin;){const char *end=strchr(line,'\n');if(!end||end>begin)end=begin;while(line<end&&(*line==' '||*line=='\t'))line++;line+=3;if(*line==' ')line++;fwrite(line,1,(size_t)(end-line),out);fputc('\n',out);line=end+1;}
    if(first<begin)fputc('\n',out);
}
static void doc_function(FILE *out,Function *f){
    fprintf(out,"### %s\n\n",f->t->text);doc_comment(out,f->t);fprintf(out,"```assis\n%sfn %s",f->pure?"pure ":f->safe&&!f->owner?"safe ":"",f->t->text);
    if(f->type_params.n){fputc('<',out);for(int i=0;i<f->type_params.n;i++){if(i)fputs(", ",out);fputs(((TypeParameter*)f->type_params.v[i])->t->text,out);}fputc('>',out);}fputc('(',out);
    if(f->receiver_mode)fprintf(out,"borrow %sself",f->receiver_mode==3?"mut ":"");
    for(int i=0;i<f->params.n;i++){Var *p=f->params.v[i];if(i||f->receiver_mode)fputs(", ",out);fprintf(out,"%s%s: %s",p->ownership==1?"own ":p->ownership==2?"borrow ":p->ownership==3?"borrow mut ":"",p->t->text,type_name(p->ty));}
    fputs("): ",out);if(f->result_mode==1)fputs("own ",out);else if(f->result_mode>=2)fprintf(out,"borrow%s(%s) ",f->result_mode==3?" mut":"",f->result_from==-1?"self":((Var*)f->params.v[f->result_from])->t->text);
    fprintf(out,"%s\n```\n\n",type_name(f->result));
}
static void document_api(const char *output){
    FILE *out=stdout;if(output){protect_output(output);out=fopen(output,"wb");if(!out)fatal("não foi possível criar documentação");}
    fprintf(out,"# API AssisScript %s\n\n",VERSION);
    for(int i=0;i<global_constants.n;i++){GlobalConstant *g=global_constants.v[i];if(documented_symbol(g->t)){doc_comment(out,g->t);fprintf(out,"```assis\nconst %s: %s\n```\n\n",g->t->text,type_name(g->ty));}}
    Vec function_groups[]={functions,generic_functions},class_groups[]={classes,generic_classes};
    for(int g=0;g<2;g++)for(int i=0;i<function_groups[g].n;i++){Function *f=function_groups[g].v[i];if(documented_symbol(f->t))doc_function(out,f);}
    for(int g=0;g<2;g++)for(int i=0;i<class_groups[g].n;i++){
        Class *c=class_groups[g].v[i];if(!documented_symbol(c->t)||c->generic)continue;
        fprintf(out,"## %s%s %s\n\n",c->sealed?"final ":"",c->tagged?"enum":c->value?"value struct":c->record?"struct":"class",c->t->text);doc_comment(out,c->t);
        for(int j=0;j<c->own_fields.n;j++){Field *f=c->own_fields.v[j];if(!f->private)fprintf(out,"- `%s%s: %s`\n",f->owned?"own ":"",f->t->text,type_name(f->ty));}
        for(int j=0;j<c->variants.n;j++){Variant *v=c->variants.v[j];fprintf(out,"- `%s",v->t->text);if(v->fields.n){fputc('(',out);for(int k=0;k<v->fields.n;k++){if(k)fputs(", ",out);fputs(type_name(((Field*)v->fields.v[k])->ty),out);}fputc(')',out);}fputs("`\n",out);}fputc('\n',out);
        for(int j=0;j<c->own_methods.n;j++){Function *f=c->own_methods.v[j];if(!f->private)doc_function(out,f);}
    }
    if(ferror(out))fatal("erro ao gerar documentação");if(output&&fclose(out))fatal("erro ao fechar documentação");
}
