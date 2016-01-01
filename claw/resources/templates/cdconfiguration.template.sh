cdconfiguration()
{
    cd {{configurations}}/$1
}

__claw_cdconfiguration_completion()
{
    COMPREPLY=( $(compgen -W "$(\ls {{configurations}})" -- \
                "${COMP_WORDS[$COMP_CWORD]}" ) )
}
complete -F __claw_cdconfiguration_completion cdconfiguration
